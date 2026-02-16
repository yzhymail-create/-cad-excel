'use strict';

const fs = require('fs/promises');
const path = require('path');

const cache = new Map();

const loadJson = async (relativePath) => {
  if (cache.has(relativePath)) {
    return cache.get(relativePath);
  }

  const fullPath = path.join(__dirname, relativePath);
  const loadPromise = fs
    .readFile(fullPath, 'utf8')
    .then((contents) => JSON.parse(contents))
    .catch((error) => {
      cache.delete(relativePath);
      if (error.code === 'ENOENT') {
        throw new Error(`缺少必需的配置文件: ${relativePath}`);
      }
      throw new Error(`无法解析配置文件 ${relativePath}: ${error.message}`);
    });

  cache.set(relativePath, loadPromise);
  return loadPromise;
};

const getAppSettings = async () => loadJson('config/app.settings.json');
const getDefaultCategories = async () => loadJson('data/default-categories.json');

module.exports = {
  getAppSettings,
  getDefaultCategories,
};
