import { Select as AntSelect, theme } from "antd";
import type { SelectProps } from "antd";
import type { CSSProperties } from "react";

type IProps<T> = {
  displayKey?: keyof T;
  valueKey?: keyof T;
  getLabel?: (item: T) => React.ReactNode;
  getValue?: (item: T) => any;
  value: Array<any>;
  placeholder: string;
  onChange: (value: T[] | Array<any>) => void;
  options: Array<T>;
  style?: CSSProperties;
  loading?: boolean;
  menuLoading?: boolean;
  returnObject?: boolean;
  clear?: boolean;
  onClearAll?: () => void;
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

const MultiSelect = <T extends object>({
  value = [],
  placeholder,
  onChange,
  options = [],
  displayKey,
  valueKey,
  getLabel,
  getValue,
  style,
  loading,
  menuLoading = false,
  popupRender,
  notFoundContent,
  returnObject = false,
  clear = true,
  onClearAll,
  ...rest
}: IProps<T>) => {
  const { token } = theme.useToken(); // get current theme

  const allStyles = style ? { ...style, width: "100%" } : { width: "100%" };

  const antOptions = options.map((item) => ({
    label: getLabel
      ? getLabel(item)
      : ((displayKey ? (item as any)[displayKey] : "") as React.ReactNode),
    value: getValue
      ? getValue(item)
      : valueKey
        ? (item as any)[valueKey]
        : undefined,
    item,
  }));

  const dropdownClass = token.colorBgContainer ? "dark-scrollbar-colors" : "";

  return (
    <AntSelect
      value={value}
      placeholder={placeholder}
      mode="multiple"
      allowClear={clear}
      onClear={() => {
        onChange([] as any);
        onClearAll?.();
      }}
      onChange={(vals, opts) => {
        if (returnObject) {
          const selected = Array.isArray(opts)
            ? opts.map((o: any) => o.item as T)
            : [];
          onChange(selected);
        } else {
          onChange(vals as any[]);
        }
      }}
      size="middle"
      style={allStyles}
      popupMatchSelectWidth={false}
      className="!w-full"
      loading={loading}
      notFoundContent={menuLoading ? <MenuSkeleton /> : notFoundContent}
      options={antOptions}
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

export default MultiSelect;
