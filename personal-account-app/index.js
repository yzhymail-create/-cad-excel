'use strict';

const fs = require('fs');
const path = require('path');

const loadJson = (relativePath) => {
  const fullPath = path.join(__dirname, relativePath);
  if (!fs.existsSync(fullPath)) {
    throw new Error(`缺少必需配置文件: ${relativePath}`);
  }
  try {
    return JSON.parse(fs.readFileSync(fullPath, 'utf8'));
  } catch (error) {
    throw new Error(`无法解析配置文件 ${relativePath}: ${error.message}`);
  }
};

const getAppSettings = () => loadJson('config/app.settings.json');
const getDefaultCategories = () => loadJson('data/default-categories.json');

module.exports = {
  getAppSettings,
  getDefaultCategories,
};
