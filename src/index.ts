import { config } from './config.js';
import { createServer } from './server.js';

const app = createServer();

app.listen(config.port, () => {
  console.log(`cold-email-reply-agent listening on :${config.port}`);
  console.log(`  webhook:  POST /webhooks/instantly`);
  console.log(`  drafts:   GET  /drafts?status=pending`);
  console.log(`  model:    ${config.anthropic.model}`);
});
