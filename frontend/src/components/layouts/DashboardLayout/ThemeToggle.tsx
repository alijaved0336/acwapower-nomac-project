import React, { useTransition } from "react";
import { Switch } from "antd";
import { SunOutlined, MoonOutlined } from "@ant-design/icons";
import { useDispatch } from "react-redux";

import { useAppSelector } from "../../../hooks";
import { toggleMode } from "@/store/feature/settingsSlice";

const ThemeToggle: React.FC = () => {
  const dispatch = useDispatch();
  const mode = useAppSelector((state) => state.settings.mode);
  const [isPending, startTransition] = useTransition();

  const handleToggle = () => {
    startTransition(() => {
      dispatch(toggleMode());
    });
  };

  return (
    <Switch
      checked={mode === "dark"}
      onChange={handleToggle}
      checkedChildren={<MoonOutlined />}
      unCheckedChildren={<SunOutlined />}
    />
  );
};

export default ThemeToggle;
