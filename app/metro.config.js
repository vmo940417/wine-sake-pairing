// 점수 엔진과 데이터는 웹 버전과 같은 파일(../web)을 쓴다.
const path = require('path');
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);
config.watchFolders = [path.resolve(__dirname, '../web')];

module.exports = config;
