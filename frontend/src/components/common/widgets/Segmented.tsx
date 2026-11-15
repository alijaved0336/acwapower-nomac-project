import { Segmented as AntSegmented } from "antd";

import type { TOption } from "@/types/misc.type";
import type { SegmentedProps } from "antd";
import type { CSSProperties, FC } from "react";

interface IProps {
  options: TOption[];
  onChange: (option: string | number) => void;
  currentOption: TOption;
  style?: CSSProperties;
  otherProps?: Omit<SegmentedProps, "options" | "value" | "onChange">;
}

const Segmented: FC<IProps> = (props) => {
  return (
    <AntSegmented
      style={{ border: "1px solid #EAECF0", ...props.style }}
      options={props.options}
      value={props.currentOption.value}
      onChange={(option) => props.onChange(option)}
      {...props.otherProps}
    />
  );
};

export default Segmented;
