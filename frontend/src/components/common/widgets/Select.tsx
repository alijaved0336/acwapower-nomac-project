import { Select as AntSelect, theme } from "antd";
import type { SelectProps } from "antd";
import type { CSSProperties, FC } from "react";
import { Virtuoso } from "react-virtuoso";
import { ArrowDownIcon } from "../../../assets/icons";
import { cn } from "../../../utils";

// Generic IProps type
type IProps<T> = {
  displayKey: keyof T; // Key to be displayed in dropdown (e.g., name)
  valueKey: keyof T; // Key to be used for the value of each option (e.g., id)
  value: T[keyof T] | undefined; // The value of the selected option
  placeholder: string; // Placeholder text for the Select component
  onChange: (value: T[keyof T]) => void; // Function to handle selection change
  options: Array<T>; // List of options with generic type T
  style?: CSSProperties; // Optional style for the Select componentimport Select from "@/components/common/widgets/Select";
  loading?: boolean; // Loading state for the Select component
  menuLoading?: boolean;
} & Omit<
  SelectProps,
  "value" | "placeholder" | "onChange" | "options" | "style" | "loading"
>;
const MenuSkeleton = ({ rows = 8 }: { rows?: number }) => (
  <div style={{ padding: 8, width: 260 }}>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} style={{ marginBottom: 8 }}>
        <div style={{ height: 32, background: "#f0f0f0", borderRadius: 6 }} />
      </div>
    ))}
  </div>
);
const Select = <T extends object>({
  value,
  placeholder,
  onChange,
  options,
  displayKey,
  valueKey,
  style,
  loading,
  menuLoading = false,
  popupRender,
  notFoundContent,
  disabled,
  ...rest
}: IProps<T>) => {
  const { token } = theme.useToken(); // get current theme

  const allStyles = style ? { ...style, width: "100%" } : { width: "100%" };

  const selectOptions = options.map((item, index) => ({
    key: index,
    value: item[valueKey] as any,
    label: item[displayKey] as React.ReactNode,
  }));

  const dropdownClass = token.colorBgContainer ? "dark-scrollbar-colors" : "";

  return (
    <AntSelect
      value={value}
      placeholder={placeholder}
      onChange={onChange}
      size="large"
      suffixIcon={<ArrowDownIcon className={cn({ "opacity-40": disabled })} />}
      style={allStyles}
      popupMatchSelectWidth={false}
      className="!w-full"
      loading={loading}
      options={selectOptions}
      virtual={true}
      listHeight={300}
      disabled={disabled}
      notFoundContent={menuLoading ? <MenuSkeleton /> : notFoundContent}
      classNames={{ popup: { root: dropdownClass } }}
      popupRender={(origin) =>
        menuLoading ? (
          <div>
            <div style={{ padding: 8, borderBottom: "1px solid #f0f0f0" }}>
              <div
                style={{ height: 16, background: "#f0f0f0", borderRadius: 4 }}
              />
            </div>
            {origin}
          </div>
        ) : popupRender ? (
          popupRender(origin)
        ) : (
          origin
        )
      }
      {...rest}
    />
  );
};

export default Select;
