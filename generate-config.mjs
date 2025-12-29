import fs from "fs";
import dotenv from "dotenv";

dotenv.config();

fs.writeFileSync(
  "config.local.js",
  `export const HOPSWORKS_API_KEY = "${process.env.HOPSWORKS_API_KEY}";`
);