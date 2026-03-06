// Jest manual mock for axios to avoid ESM entrypoint issues.
// It re-exports the CommonJS build so existing axios usage keeps working.

// eslint-disable-next-line @typescript-eslint/no-var-requires
const axios = require('axios/dist/node/axios.cjs');

module.exports = axios;
module.exports.default = axios;

