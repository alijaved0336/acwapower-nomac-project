"use client";

import { Avatar, Dropdown } from "antd";
import { useEffect, useState } from "react";
import { colorToken } from "@/styles/themes/tokens/colors";
import { generateInitials, isValidImageUrl } from "@/utils/userUtils";
import { BackendUser } from "../../../types/api.types";
import { useUserMenu } from "@/hooks/useUserMenu";
import { useAppSelector } from "../../../hooks";

interface CompactMenuOptionProps {
  collapsed: boolean;
}

export const CompactMenuOption: React.FC<CompactMenuOptionProps> = ({
  collapsed,
}) => {
  const [user, setUser] = useState<BackendUser | null>(null);
  const currentUser = useAppSelector((state) => state.auth.user);

  useEffect(() => {
    setUser(currentUser);
  }, [currentUser]);

  const menuItems = useUserMenu();

  if (collapsed) {
    // Collapsed view - just avatar
    return (
      <Dropdown
        menu={{ items: menuItems }}
        placement="bottomRight"
        trigger={["click"]}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            cursor: "pointer",
          }}
        >
          <Avatar
            alt="profileImage"
            src={isValidImageUrl(user?.picture) ? user?.picture : undefined}
            style={{
              width: "40px",
              height: "40px",
              backgroundColor: !isValidImageUrl(user?.picture)
                ? colorToken?.colorPrimary
                : undefined,
              color: !isValidImageUrl(user?.picture) ? "#fff" : undefined,
              fontSize: "14px",
              fontWeight: "600",
            }}
          >
            {!isValidImageUrl(user?.picture) &&
              generateInitials(user?.name || "")}
          </Avatar>
        </div>
      </Dropdown>
    );
  }

  // Expanded view - use the original MenuOption
  return null;
};
