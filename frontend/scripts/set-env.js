const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables from .env file if it exists
dotenv.config();

const envConfigFile = `export const environment = {
  production: true,
  clerkPublishableKey: '${process.env.CLERK_PUBLISHABLE_KEY}',
  apiUrl: 'https://timeopti.onrender.com'
};
`;

const targetPath = path.join(__dirname, '../src/environments/environment.prod.ts');
const targetPathDev = path.join(__dirname, '../src/environments/environment.ts');

// Ensure the directory exists
const dirPath = path.dirname(targetPath);
if (!fs.existsSync(dirPath)) {
  fs.mkdirSync(dirPath, { recursive: true });
  console.log(`Created directory: ${dirPath}`);
}

// Generate environment.prod.ts
fs.writeFile(targetPath, envConfigFile, function (err) {
  if (err) {
    console.log(err);
  }
  console.log(`Output generated at ${targetPath}`);
});

// Generate environment.ts
const envConfigFileDev = `export const environment = {
  production: false,
  clerkPublishableKey: '${process.env.CLERK_PUBLISHABLE_KEY}',
  apiUrl: 'http://localhost:8000'
};
`;

fs.writeFile(targetPathDev, envConfigFileDev, function (err) {
  if (err) {
    console.log(err);
  }
  console.log(`Output generated at ${targetPathDev}`);
});
