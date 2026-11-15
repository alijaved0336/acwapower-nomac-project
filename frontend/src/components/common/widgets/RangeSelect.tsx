import React from "react";
import Select from "./Select";
import { SelectProps } from "antd";

type RangeSelectProps = {
  label: string; // "Min" or "Max"
  value?: number;
  range: number[];
  onChange: (val: number) => void;
} & SelectProps;

const RangeSelect: React.FC<RangeSelectProps> = ({
  label,
  value,
  range,
  onChange,
  ...rest
}) => {
  const mappedValues = range.map((v) => ({ value: v, label: v.toString() }));

  return (
    <Select
      {...rest}
      style={{ width: 120 }}
      placeholder={`${label}`}
      value={value}
      displayKey="label"
      valueKey="value"
      onChange={(v) => onChange(v as number)}
      options={mappedValues}
      showSearch
    />
  );
};

export default RangeSelect;
