import { Collapse as AntCollapse, CollapseProps } from "antd";
import React, { FC, ReactNode } from "react";
import styled from "styled-components";

export const CollapseContainer = styled.div`
  /* .ant-collapse-content-box { */
  max-height: 25vh;
  overflow-x: hidden;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 8px;
  }
  &::-webkit-scrollbar-thumb {
    background: #bfbfbf;
    border-radius: 4px;
  }
  &::-webkit-scrollbar-thumb:hover {
    background: #8c8c8c;
  }
  &::-webkit-scrollbar-track {
    background: #f0f0f0;
  }

  scrollbar-width: thin;
  scrollbar-color: #bfbfbf #f0f0f0;
`;

type CustomCollapseProps = {
  children: ReactNode;
} & CollapseProps;

const Collapse: FC<CustomCollapseProps> = ({ children, ...rest }) => {
  return <AntCollapse {...rest}>{children}</AntCollapse>;
};

export default Collapse;
