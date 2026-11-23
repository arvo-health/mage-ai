import React, { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { ThemeProvider } from 'styled-components';

import dark from '@oracle/styles/themes/dark';

import { COOKIE_KEY, getToken, setToken } from '@api/utils/token';
import CodeOutput from '@components/CodeBlock/CodeOutput';
import HTMLOutput from '@components/CodeBlock/CodeOutput/HTMLOutput';
import OutputRenderer from '@components/CodeBlock/CodeOutput/OutputRenderer';
import TableOutput from '@components/CodeBlock/CodeOutput/TableOutput';
import useCodeOutput from '@components/CodeBlock/CodeOutput/useCodeOutput';
import { prepareOutputsForDisplay } from '@components/PipelineDetail/utils';
import { DataTypeEnum } from '@interfaces/KernelOutputType';

declare global {
  interface Window {
    __case?: string;
    __cookieReadable?: boolean;
    __fixtures?: any;
    __mageXss?: number;
    __renderDone?: boolean;
    __renderError?: string;
  }
}

const MARK = 'placeholder-session';

function blockWith(outputs) {
  return {
    color: null,
    name: 'block_a',
    outputs,
    status: 'executed',
    type: 'transformer',
    uuid: 'block_a',
  };
}

function UseCodeOutputProbe({ messages }) {
  const { textContent } = useCodeOutput({
    block: blockWith([]),
    hasOutput: true,
    isInProgress: false,
    messages,
    pipeline: { uuid: 'pipe' },
  });
  return <div id="use-code-output">{textContent}</div>;
}

function App() {
  const fixtures = window.__fixtures;
  const scriptTable = fixtures.table_script;
  const handlerTable = fixtures.table_handler;
  const listTable = fixtures.list_script;
  const kernel = fixtures.kernel_html;
  const name = window.__case;
  const preparedSingle = prepareOutputsForDisplay([scriptTable]);
  const preparedHandler = prepareOutputsForDisplay([handlerTable]);
  const preparedList = prepareOutputsForDisplay([listTable]);
  useEffect(() => {
    if (name === 'cookie') {
      setToken(MARK);
      const cookieText = document.cookie || '';
      const readable = cookieText.split('; ').some((part) => part.startsWith(`${COOKIE_KEY}=`))
        || Boolean(getToken());
      window.__cookieReadable = readable;
    }
    window.__renderDone = true;
  }, [name]);

  if (name === 'cookie') {
    return <div id="cookie" />;
  }
  if (name === 'code-output-single-script') {
    return (
      <CodeOutput
        block={blockWith([scriptTable])}
        hasOutput
        isInProgress={false}
        messages={preparedSingle}
        pipeline={{ uuid: 'pipe', type: 'python' }}
      />
    );
  }
  if (name === 'code-output-single-handler') {
    return (
      <CodeOutput
        block={blockWith([handlerTable])}
        hasOutput
        isInProgress={false}
        messages={preparedHandler}
        pipeline={{ uuid: 'pipe', type: 'python' }}
      />
    );
  }
  if (name === 'code-output-list') {
    return (
      <CodeOutput
        block={blockWith([listTable])}
        hasOutput
        isInProgress={false}
        messages={preparedList}
        pipeline={{ uuid: 'pipe', type: 'python' }}
      />
    );
  }
  if (name === 'code-output-html-message') {
    return (
      <CodeOutput
        block={blockWith([])}
        hasOutput
        isInProgress={false}
        messages={[{
          data: kernel.data,
          type: kernel.type,
          variable_uuid: 'kernel',
        }]}
        pipeline={{ uuid: 'pipe', type: 'python' }}
      />
    );
  }
  if (name === 'renderer-html') {
    return (
      <OutputRenderer
        block={blockWith([])}
        output={{
          text_data: kernel.data,
          type: DataTypeEnum.TEXT_HTML,
          variable_uuid: 'kernel-renderer',
        }}
        selected={false}
      />
    );
  }
  if (name === 'html-output') {
    return <HTMLOutput value={kernel.data} />;
  }
  if (name === 'table-output') {
    return <TableOutput output={scriptTable} selected={false} />;
  }
  if (name === 'use-code-output') {
    return (
      <UseCodeOutputProbe
        messages={[{
          data: kernel.data,
          type: kernel.type,
          variable_uuid: 'kernel-hook',
        }]}
      />
    );
  }
  return <div />;
}

const root = createRoot(document.getElementById('root'));
try {
  root.render(
    <ThemeProvider theme={dark}>
      <App />
    </ThemeProvider>,
  );
} catch (error) {
  window.__renderError = String(error);
  window.__renderDone = true;
}
