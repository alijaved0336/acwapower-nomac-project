import React, { FC, ReactNode } from "react";

import { Radio, RadioProps } from "antd";

import styled from "styled-components";

const StyledRadio = styled(Radio)`
  cursor: pointer;

  /* Remove Ant Design default dot */
  .ant-radio-inner {
    display: none !important;
  }
`;

type RadioCardProps = {
  children: ReactNode;
} & RadioProps;

const RadioItem: FC<RadioCardProps> = ({ children, ...rest }) => {
  return (
    <>
      <StyledRadio {...rest}>{children}</StyledRadio>
    </>
  );
};

export default RadioItem;
