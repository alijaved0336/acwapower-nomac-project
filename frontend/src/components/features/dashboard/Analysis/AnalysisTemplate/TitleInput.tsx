import React, {
  FC,
  memo,
  useCallback,
  useDeferredValue,
  useEffect,
  useState,
} from "react";
import { cn } from "../../../../../utils";
import { debounce } from "lodash";

type TitleInputProps = {
  value: string;
  onChange: (value: string) => void;
  className?: string;
};

const TitleInput: FC<TitleInputProps> = ({ value, className, onChange }) => {
  const [debouncedValue, setDebouncedValue] = useState(() => value);

  useEffect(() => {
    setDebouncedValue(value);
  }, [value]);

  const debouncedSearch = useCallback(
    debounce((value) => {
      onChange(value);
    }, 500), // 500ms delay
    []
  );

  // Handle input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDebouncedValue(e.target.value);
    debouncedSearch(e.target.value);
  };

  return (
    <input
      className={cn(
        "tw-bg-transparent text-text-base border-b border-gray-300 text-xl font-semibold focus:outline-none",
        className
      )}
      value={debouncedValue}
      onChange={handleChange}
    />
  );
};

export default memo(TitleInput);
