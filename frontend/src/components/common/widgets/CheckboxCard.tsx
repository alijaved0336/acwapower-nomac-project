import React, { FC, ReactNode } from "react";

import { Checkbox, CheckboxProps } from "antd";

import styled from "styled-components";

const StyledCheckboxCard = styled(Checkbox)`
  width: 100%;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid var(--color-gray-4);
  background-color: #fff;

  cursor: pointer;

  &.ant-radio-wrapper {
    border: 1px solid rgba(30, 30, 30, 0.07);
  }

  /* Checked State */
  &.ant-radio-wrapper-checked {
    border: 1px solid var(--color-turmeric-6);
  }
`;

type CheckboxCardProps = {
  children: ReactNode;
} & CheckboxProps;

const CheckboxCard: FC<CheckboxCardProps> = ({ children, ...rest }) => {
  return (
    <>
      <StyledCheckboxCard {...rest}>{children}</StyledCheckboxCard>
    </>
  );
};

export default CheckboxCard;
