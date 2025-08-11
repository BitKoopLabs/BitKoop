import asyncio
import json
import os
import subprocess
import tempfile
import logging
import contextlib
from datetime import UTC, datetime
from pathlib import Path
from typing import List, Tuple, Callable, Optional

from subnet_validator.constants import CouponStatus
from subnet_validator.database.entities import Coupon, Site


logger = logging.getLogger(__name__)


class PlaywrightCouponValidator:
    def __init__(self, site: Site, path: Path):
        self.site = site
        self.node_script_path = path
        
    async def _stream_subprocess_output(self, stream: asyncio.StreamReader, level: int, prefix: str, on_line: Optional[Callable[[str], None]] = None) -> None:
        """Stream subprocess output line-by-line to logger, calling on_line for each decoded line if provided."""
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                try:
                    text = line.decode(errors="replace").rstrip()
                except Exception:
                    text = str(line)
                logger.log(level, "%s%s", prefix, text)
                if on_line is not None:
                    try:
                        on_line(text)
                    except Exception as cb_err:
                        logger.debug("on_line callback raised: %s", cb_err)
        except Exception as e:
            logger.warning("Error while streaming subprocess output: %s", e)

    async def _run_node_validation(self, coupon: Coupon, site_config: dict) -> bool:
        """Run the Node.js validation script as a subprocess"""
        try:
            # Create temporary directory for output
            with tempfile.TemporaryDirectory() as temp_dir:
                # Prepare the command
                config_arg = json.dumps(site_config, ensure_ascii=False, separators=(",", ":"))
                cmd = [
                    "node",
                    str(self.node_script_path),
                    f"--coupon={coupon.code}",
                    f"--domain={self.site.base_url}",
                    f"--config={config_arg}",
                ]
                if coupon.used_on_product_url:
                    cmd.append(f"--used_on_product_url={coupon.used_on_product_url}")
                logger.info(
                    "Starting Node.js validation subprocess: cmd=%s, cwd=%s, coupon=%s, domain=%s",
                    " ".join(map(str, cmd)),
                    temp_dir,
                    coupon.code,
                    self.site.base_url,
                )

                # Run the subprocess
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=temp_dir
                )
                # Stream stdout/stderr in real time
                success_seen = False

                def check_success(line: str) -> None:
                    nonlocal success_seen
                    if ("Coupon is valid" in line) or ("🎉" in line):
                        success_seen = True

                stdout_task = asyncio.create_task(
                    self._stream_subprocess_output(process.stdout, logging.INFO, "node(stdout): ", on_line=check_success)
                )
                stderr_task = asyncio.create_task(
                    self._stream_subprocess_output(process.stderr, logging.ERROR, "node(stderr): ")
                )

                try:
                    await asyncio.wait_for(process.wait(), timeout=300)  # 5 minute timeout
                except asyncio.TimeoutError:
                    logger.error("Subprocess timed out after 300s. Terminating...")
                    with contextlib.suppress(ProcessLookupError):
                        process.kill()
                    # Ensure we consume remaining output
                    await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
                    return False

                # Ensure all output was drained
                await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)

                logger.info("Subprocess finished with return code %s", process.returncode)
                if process.returncode != 0:
                    logger.error("Node.js script exited with non-zero return code: %s", process.returncode)
                    return False
                
                # Check if result.json was created and parse it
                result_file = Path(temp_dir) / "output" / "result.json"
                if result_file.exists():
                    with open(result_file, 'r') as f:
                        result = json.load(f)
                        return result.get("couponIsValid", False)
                
                # Fallback: check stdout for success indicators
                logger.debug("Result file not found. Falling back to success indicators in streamed output.")
                return success_seen
                
        except Exception as e:
            logger.exception("Error running Node.js validation: %s", e)
            return False

    async def validate(self, coupons: List[Coupon]) -> List[Tuple[Coupon, bool]]:
        """Validate coupons using the Node.js Playwright script"""
        results = []
        
        for coupon in coupons:
            try:
                # Create site configuration
                
                # Run validation
                config = self.site.config.copy()
                if coupon.used_on_product_url:
                    config["productUrl"] = coupon.used_on_product_url
                is_valid = await self._run_node_validation(coupon, config)
                
                # Update coupon status
                coupon.status = CouponStatus.VALID if is_valid else CouponStatus.INVALID
                coupon.last_checked_at = datetime.now(UTC)
                
                results.append((coupon, is_valid))
                
            except Exception as e:
                logger.exception("Error validating coupon %s: %s", coupon.code, e)
                coupon.status = CouponStatus.INVALID
                coupon.last_checked_at = datetime.now(UTC)
                results.append((coupon, False))
        
        return results

