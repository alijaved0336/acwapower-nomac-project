import { Input } from "antd";
import React, { FC, useCallback, useState } from "react";
import { SearchOutlined } from "@ant-design/icons";
import { debounce } from "lodash";

type SearchInputProps = {
  className?: string;
  onSearch: (value: string) => void;
  placeholder?: string;
};

const SearchInput: FC<SearchInputProps> = ({
  className,
  onSearch,
  placeholder = "Search...",
}) => {
  const [searchQuery, setSearchQuery] = useState("");

  // Debounced search function
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const debouncedSearch = useCallback(
    debounce((value) => {
      onSearch(value);
    }, 500), // 500ms delay
    []
  );

  // Handle input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    debouncedSearch(e.target.value);
  };

  return (
    <Input
      allowClear
      prefix={<SearchOutlined />}
      placeholder={placeholder}
      value={searchQuery}
      onChange={handleChange}
      className={className}
    />
  );
};

export default SearchInput;
