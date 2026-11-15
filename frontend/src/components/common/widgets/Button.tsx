import { Button as AntButton } from "antd";

import type { ButtonProps } from "antd";
import type { CSSProperties, FC, PropsWithChildren, ReactNode } from "react";

interface IProps {
  content: ReactNode;
  loading?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  type?: ButtonProps["type"];
  variant?: ButtonProps["variant"];
  danger?: boolean;
  icon?: ReactNode;
  size?: "small" | "middle" | "large";
  style?: CSSProperties;
  otherProps?: Omit<
    ButtonProps,
    | "text"
    | "loading"
    | "disabled"
    | "onClick"
    | "type"
    | "icon"
    | "size"
    | "style"
    | "danger"
    | "variant"
  >;
}

const Button: FC<PropsWithChildren<IProps>> = (props) => {
  return (
    <AntButton
      loading={props.loading ?? false}
      disabled={props.disabled ?? false}
      onClick={props.onClick}
      type={props.type ?? "default"}
      variant={props.variant ?? "outlined"}
      danger={props.danger ?? false}
      icon={props.icon}
      size={props.size}
      style={props.style}
      {...props.otherProps}
    >
      {props.content}
    </AntButton>
  );
};

export default Button;
