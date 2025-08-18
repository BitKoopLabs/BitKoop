## BitKoop Mining Guide

This short guide explains what a miner needs to do to participate in the BitKoop subnet.

---

### 1) Register your hotkey on the subnet

Register your hotkey on the subnet using the Bittensor CLI:

```sh
btcli subnet register --netuid 16
```

---

### 2) Miner tasks

- Submit discount codes
  - Up to 3 active codes per website per miner
  - Provide helpful metadata where possible: validity period, category, country, restrictions, and product URL (same domain)
  - Keep submissions fresh and genuine; expired or non-working codes will be marked INVALID by validators

- Maintain your codes
  - Recheck previously INVALID codes after cooldown if you believe they became valid again
  - Delete codes that are no longer valid to keep the dataset clean

- Monitor performance
  - Track your rank and scores over time; recent, working codes improve your normalized weight

Interface: Use the BitKoop Miner CLI to interact with validators

- Repository: `https://github.com/BitKoop-com/BitKoop-CLI`
- Install and follow its usage guide for commands to submit, recheck, delete codes, list sites/categories, and check ranks
- The CLI uses your Bittensor wallet configuration for authenticated operations

---

### 3) JSON configuration creation and maintenance (future; not implemented yet)

You will be able to submit a per-website JSON configuration that validators use to test promo codes.

Two execution modes will be supported: fully automated real-user flow simulation or direct API request.

Details and templates will be published later.

#### How we plan it will work

- Download the Node.js project with the validation script.
- Create a JSON file for your target website.
- Add an `events` object that defines the automated flow to:
  - add an item to cart
  - proceed through checkout
  - reveal the coupon input field
  Each step will include a selector and an action (`click`, `select`, `fill`).
- Add a `resultCheck` object with:
  - a selector where the script can read the outcome text
  - unique text pattern that indicate “valid” coupon state
- Test locally with a real, working code before submitting.


