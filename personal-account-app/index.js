'use strict';

const fs = require('fs/promises');
const path = require('path');

const cache = new Map();

const loadJson = async (relativePath) => {
  if (cache.has(relativePath)) {
    return cache.get(relativePath);
  }

  const fullPath = path.join(__dirname, relativePath);
  let contents;
  try {
    contents = await fs.readFile(fullPath, 'utf8');
  } catch (error) {
    if (error.code === 'ENOENT') {
      throw new Error(`缺少必需的配置文件: ${relativePath}`);
    }
    throw new Error(`无法读取配置文件 ${relativePath}: ${error.message}`);
  }

  try {
    const parsed = JSON.parse(contents);
    cache.set(relativePath, parsed);
    return parsed;
  } catch (error) {
    throw new Error(`配置文件 ${relativePath} JSON 格式错误: ${error.message}`);
  }
};

const getAppSettings = async () => loadJson('config/app.settings.json');
const getDefaultCategories = async () => loadJson('data/default-categories.json');

module.exports = {
  getAppSettings,
  getDefaultCategories,
};
