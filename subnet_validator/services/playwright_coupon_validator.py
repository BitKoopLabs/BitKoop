import asyncio
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import List, Tuple

from subnet_validator.constants import CouponStatus
from subnet_validator.database.entities import Coupon, Site


class PlaywrightCouponValidator:
    def __init__(self, site: Site, path: Path):
        self.site = site
        self.node_script_path = path
        
    async def _run_node_validation(self, coupon: Coupon, site_config: dict) -> bool:
        """Run the Node.js validation script as a subprocess"""
        try:
            # Create temporary directory for output
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create temporary config file to avoid command line escaping issues
                config_file = Path(temp_dir) / "config.json"
                with open(config_file, 'w') as f:
                    json.dump(site_config, f, ensure_ascii=False)
                
                # Prepare the command
                cmd = [
                    "node",
                    str(self.node_script_path),
                    f"--coupon={coupon.code}",
                    f"--domain={self.site.base_url}",
                    f"--config={json.dumps(site_config, ensure_ascii=False)}",
                    f"--used_on_product_url={coupon.used_on_product_url}" if coupon.used_on_product_url else None
                ]
                
                # Run the subprocess
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=temp_dir
                )
                
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)  # 5 minute timeout
                
                if process.returncode != 0:
                    print(f"Node.js script error: {stderr.decode()}")
                    return False
                
                # Check if result.json was created and parse it
                result_file = Path(temp_dir) / "output" / "result.json"
                if result_file.exists():
                    with open(result_file, 'r') as f:
                        result = json.load(f)
                        return result.get("couponIsValid", False)
                
                # Fallback: check stdout for success indicators
                output = stdout.decode()
                return "Coupon is valid" in output or "🎉" in output
                
        except asyncio.TimeoutError:
            print(f"Validation timeout for coupon {coupon.code}")
            return False
        except Exception as e:
            print(f"Error running Node.js validation: {e}")
            return False

    async def validate(self, coupons: List[Coupon]) -> List[Tuple[Coupon, bool]]:
        """Validate coupons using the Node.js Playwright script"""
        results = []
        
        for coupon in coupons:
            try:
                # Create site configuration
                
                # Run validation
                config = self.site.config
                is_valid = await self._run_node_validation(coupon, config)
                
                # Update coupon status
                coupon.status = CouponStatus.VALID if is_valid else CouponStatus.INVALID
                coupon.last_checked_at = datetime.now(UTC)
                
                results.append((coupon, is_valid))
                
            except Exception as e:
                print(f"Error validating coupon {coupon.code}: {e}")
                coupon.status = CouponStatus.INVALID
                coupon.last_checked_at = datetime.now(UTC)
                results.append((coupon, False))
        
        return results

