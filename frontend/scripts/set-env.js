const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables from .env file if it exists
dotenv.config();

const envConfigFile = `export const environment = {
  production: true,
  clerkPublishableKey: '${process.env.CLERK_PUBLISHABLE_KEY}'
};
`;

const targetPath = path.join(__dirname, '../src/environments/environment.prod.ts');
const targetPathDev = path.join(__dirname, '../src/environments/environment.ts');

// Generate environment.prod.ts
fs.writeFile(targetPath, envConfigFile, function (err) {
    if (err) {
        console.log(err);
    }
    console.log(`Output generated at ${targetPath}`);
});

// Generate environment.ts (for dev compatibility if needed, though usually dev has its own)
// For now, we'll make them identical for simplicity in this fix, or we can check NODE_ENV
const envConfigFileDev = `export const environment = {
  production: false,
  clerkPublishableKey: '${process.env.CLERK_PUBLISHABLE_KEY}'
};
`;

fs.writeFile(targetPathDev, envConfigFileDev, function (err) {
    if (err) {
        console.log(err);
    }
    console.log(`Output generated at ${targetPathDev}`);
});
