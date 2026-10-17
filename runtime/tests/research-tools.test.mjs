import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {once} from 'node:events';
import {Agent, setGlobalDispatcher} from 'undici';
import {requestTool} from '../runtime/adapter/bridge-request.mjs';

class RecordingAgent extends Agent {
  dispatch(options, handler) {
    this.options = options;
    return super.dispatch(options, handler);
  }
}

async function setup(t, handler) {
  const server = createServer(handler).listen(8098, '127.0.0.1');
  await once(server, 'listening');
  const dispatcher = new RecordingAgent();
  setGlobalDispatcher(dispatcher);
  t.after(async () => {server.closeAllConnections(); server.close(); await dispatcher.destroy();});
  process.env.RW_TOOL_TOKEN = 'test-binding';
  return {dispatcher};
}

const args = {tasks: [{instructions: 'review', task: 'review', thinking: 'high'}]};

test('delegate transport disables hidden header and body deadlines', async t => {
  const {dispatcher} = await setup(t, (_req, res) => {
    setTimeout(() => res.end('{"results":[{"status":"completed"}]}'), 30);
  });
  const result = await requestTool('delegate', args, new AbortController().signal);
  assert.equal(result.results[0].status, 'completed');
  assert.equal(dispatcher.options.headersTimeout, 0);
  assert.equal(dispatcher.options.bodyTimeout, 0);
});

test('waiting delegate remains cancellable', async t => {
  let received;
  const incoming = new Promise(resolve => {received = resolve;});
  await setup(t, () => received());
  const controller = new AbortController();
  const result = requestTool('delegate', args, controller.signal);
  const rejected = assert.rejects(result, error => error.name === 'AbortError');
  await incoming;
  controller.abort();
  await rejected;
});
