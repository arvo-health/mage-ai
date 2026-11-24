import React from 'react';

import SanitizedHTML from '@components/shared/SanitizedHTML';
import { OutputRowStyle, HTMLOutputStyle, OutputRowProps } from './index.style';

type HTMLOutputProps = {
  value: string;
} & OutputRowProps;

function HTMLOutput({ value, ...outputRowSharedProps }: HTMLOutputProps) {
  return (
    <OutputRowStyle {...outputRowSharedProps}>
      <HTMLOutputStyle monospace>
        <SanitizedHTML html={value} />
      </HTMLOutputStyle>
    </OutputRowStyle>
  );
}

export default HTMLOutput;
