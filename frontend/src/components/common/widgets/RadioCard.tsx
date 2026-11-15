import React, { FC, ReactNode } from "react";

import { Radio, RadioProps, theme } from "antd";

type RadioCardProps = {
  children: ReactNode;
} & RadioProps;

const RadioCard: FC<RadioCardProps> = ({ children, ...rest }) => {
  const { token } = theme.useToken();

  return (
    <Radio
      {...rest}
      style={{
        width: "100%",
        padding: "16px",
        borderRadius: "8px",
        border: rest.checked
          ? `1px solid ${token.colorPrimary}`
          : `1px solid ${token.colorBorder}`,
        backgroundColor: token.colorBgContainer,
        cursor: "pointer",
        transition: "all 0.3s",
      }}
      className={rest.className}
    >
      {children}
    </Radio>
  );
};

export default RadioCard;
