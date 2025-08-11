## BitKoop Validator Setup Guide

This guide will walk you through setting up a BitKoop validator node.

Note: For subnet registration and system overview, see the main README.

---

## 🟢 Quick Start: Remote Docker Compose Setup

1. Create a new directory for the validator and enter it:

   ```sh
   mkdir BitKoop
   cd BitKoop
   ```

2. Download the latest `docker-compose.yml` from the official repository:

   ```sh
   curl -L -o docker-compose.yml https://raw.githubusercontent.com/BitKoop-com/BitKoop/main/docker-compose.yml
   ```

3. Start the validator (and watchtower) in the background:

   ```sh
   docker compose up -d
   ```

   ⚠️ Warning: By default, the validator will use the wallet name `default` and hotkey `default`. It is strongly recommended to set your own wallet name and hotkey for security and proper operation. See Wallet Customization below for instructions.

   Tip: You can customize the port by setting the `PORT` environment variable, either in your `.env` file or directly when starting Docker Compose:

   ```sh
   PORT=9000 docker compose up -d
   ```

   Or edit the `PORT` value in your `.env` file. This is the recommended way to change the port (default is `8000`).

4. Post your external IP and port to the chain (required for network participation):

   ```sh
   docker compose exec bitkoop-validator fiber-post-ip \
     --netuid <NETUID> \
     --external_ip <YOUR_IP> \
     --external_port <YOUR_PORT>
   ```

   - See the Fiber Post IP to Chain documentation for more details and command options: `https://fiber.sn19.ai/how-it-works/post-ip-to-chain/`.
   - Make sure the port you specify is open and forwarded to your machine if behind NAT/firewall.

5. Check if it's running:

   Use the following command to check a simple info endpoint from your VPS (replace `$PORT` with your configured port if different):

   ```sh
   curl http://localhost:${PORT:-8000}/info/sync
   ```

   You should see a JSON response containing fields like `progress` and `last_result`.

---

## 🛑 Alternative: Running Locally (Not Recommended)

- The recommended way to run the validator is with Docker Compose.
- Running locally is only for advanced users who need to run outside Docker.
- There is no autoupdate support when running locally.

If you still want to run locally:

1. Clone the repository and set up your environment:

   ```sh
   git clone https://github.com/BitKoop-com/BitKoop.git
   cd BitKoop
   python3 -m venv venv
   source venv/bin/activate
   pip install .
   ```

2. Create your environment file:

   ```sh
   cp env.example .env
   # then edit .env to set WALLET_NAME, WALLET_HOTKEY, and other variables
   ```

3. Run database migrations and start the API:

   ```sh
   alembic upgrade head
   uvicorn subnet_validator.main:app --host 0.0.0.0 --port ${PORT:-8000}
   ```

4. (Optional) Start background tasks in a separate process or terminal:

   ```sh
   python -m subnet_validator.tasks.run_tasks
   ```

---

## ⚙️ Wallet Customization

You must set your Bittensor wallet name and hotkey for the validator to function correctly. There are two recommended ways to do this:

### 1. Using a `.env` File (Recommended)

1. Copy the example environment file and rename it:

   ```sh
   cp env.example .env
   ```

2. Open `.env` in your editor and fill in your wallet details:

   ```env
   WALLET_NAME=my_wallet
   WALLET_HOTKEY=my_hotkey
   # You can add other variables as needed
   ```

3. Start Docker Compose as usual:

   ```sh
   docker compose up -d
   ```

   The validator will automatically use the values from your `.env` file.

See the `env.example` file for all available variables you can set.

### 2. Overriding via Command Line

You can also override these variables directly when starting Docker Compose:

```sh
WALLET_NAME=my_wallet WALLET_HOTKEY=my_hotkey docker compose up -d
```

Replace `my_wallet` and `my_hotkey` with your actual wallet name and hotkey.

---

## Configuration

Most settings can be changed via environment variables used by `docker-compose.yml`:

- `PORT`: API port (default `8000`)
- `WALLET_NAME`, `WALLET_HOTKEY`, `WALLET_PATH`: Your Bittensor wallet info
- `SUBTENSOR_NETWORK`: Bittensor network (e.g., `finney`)
- `PROXY_SERVER`, `PROXY_USERNAME`, `PROXY_PASSWORD`: Optional proxy for validation tasks

---

## Requirements

- Docker and Docker Compose
- (Advanced) Python 3.9+ if running without Docker


