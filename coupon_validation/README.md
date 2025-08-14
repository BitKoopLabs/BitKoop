# 🏷️ Coupon Validator

This project uses [Playwright](https://playwright.dev) to automate the process of testing coupons on various websites. The script opens a browser, performs a series of actions, and applies a coupon code on a product or checkout page.

## 📁 Project Structure

```
coupon_project/
├── index.js               # Main automation script
├── actions.json           # JSON file describing actions for each domain
├── package.json           # Project metadata and dependencies
```

## 🚀 Installation

1. Clone the repository or unzip the archive.
2. Install dependencies:

```bash
npm install
```

3. Install Playwright browsers (if not already installed):

```bash
npx playwright install
```

## ▶️ Usage

Run the script with CLI parameters:

```bash
node index.js --coupon=MYCOUPON --domain=example.com
```


Then start with:

```bash
npm start
```

## ⚙️ Defining Actions

The `actions.json` file defines actions for different websites. Example:

```json
{
  "example.com": {
    "productUrl": "https://example.com/product",
    "actions": [
      {
        "name": "addToCart",
        "selectors": ["#addToCart"],
        "type": "click",
        "waitAfter": 5000,
        "event": "[🛒] Adding product to cart..."
      }
    ]
  }
}
```

Each action can include:
- `name`: Logical name of the step
- `selectors`: List of CSS selectors to try
- `type`: `click`, `fill`, etc.
- `waitAfter`: Delay after action (in ms)
- `event`: Optional log message

## 🧪 Debug Mode

To run the browser in visible (non-headless) mode for debugging, change this line in `index.js`:

```js
const browser = await firefox.launch({ headless: false });
```

---

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
