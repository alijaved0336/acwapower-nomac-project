import { Spin, SpinProps } from "antd";
import React, { FC } from "react";
import { cn } from "../../utils/cn";

type SpinnerProps = {
  className?: string;
} & SpinProps;

const Spinner: FC<SpinnerProps> = ({ className, ...rest }) => {
  return (
    <div
      className={cn(
        "flex w-full items-center justify-center opacity-50",
        className
      )}
    >
      <Spin {...rest} />
    </div>
  );
};

export default Spinner;
