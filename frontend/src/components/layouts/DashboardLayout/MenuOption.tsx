"use client";

import { Avatar, Flex, Grid, Typography, Skeleton, Dropdown, Menu } from "antd";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { colorToken } from "@/styles/themes/tokens/colors";
import { sizeToken } from "@/styles/themes/tokens/size";
import { NotificationIcon, SettingIcon } from "@/assets/icons";

import { generateInitials, isValidImageUrl } from "@/utils/userUtils";
import { BackendUser } from "../../../types/api.types";
import { DownOutlined } from "@ant-design/icons";
import { useUserMenu } from "@/hooks/useUserMenu";
import { useAppSelector } from "../../../hooks";

const { useBreakpoint } = Grid;

export const MenuOption = () => {
  const pathname = usePathname();
  const isActive = pathname === "/settings";
  const size = useBreakpoint();
  const [user, setUser] = useState<BackendUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const currentUser = useAppSelector((state) => state.auth.user);

  const logoColor = isActive ? "#005d99" : "black";

  useEffect(() => {
    // Get current user from token service
    setUser(currentUser);
    setIsLoading(false);
  }, [currentUser]);

  const menuItems = useUserMenu();

  const handleMenuClick = (info: any) => {
    // Don't close dropdown if clicking on refresh submenu items
    if (info?.key?.toString().startsWith("refresh-")) {
      return;
    }
    // Close dropdown for other menu items
    setDropdownOpen(false);
  };

  return (
    <Flex align="center" gap={sizeToken.size}>
      {/* <Link
        href={"/settings"}
        style={{ display: "flex", alignItems: "center" }}
      >
        <SettingIcon width={20} height={20} stroke={logoColor} />
      </Link> */}

      {/* <Link
        href={"/notifications"}
        style={{ display: "flex", alignItems: "center" }}
      >
        <NotificationIcon width={20} height={20} stroke={logoColor} />
      </Link> */}
      <Dropdown
        menu={{
          items: menuItems,
          onClick: handleMenuClick,
          triggerSubMenuAction: "click",
        }}
        placement="bottomRight"
        trigger={["click"]}
        open={dropdownOpen}
        onOpenChange={setDropdownOpen}
      >
        <Flex
          align="center"
          gap={sizeToken.sizeXS}
          style={{
            cursor: "pointer",
            padding: "6px 12px",
            borderRadius: "8px",
            transition: "all 0.2s ease",
          }}
          className="user-dropdown-trigger"
          onMouseEnter={(e) =>
            (e.currentTarget.style.background = "rgba(0, 0, 0, 0.04)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.background = "transparent")
          }
        >
          <Avatar
            alt="profileImage"
            src={isValidImageUrl(user?.picture) ? user?.picture : undefined}
            style={{
              width: "2.5rem",
              height: "2.5rem",
              backgroundColor: !isValidImageUrl(user?.picture)
                ? colorToken?.colorPrimary
                : undefined,
              color: !isValidImageUrl(user?.picture) ? "#fff" : undefined,
              fontSize: "0.875",
              fontWeight: "600",
              padding: "14px",
            }}
          >
            {!isValidImageUrl(user?.picture) &&
              generateInitials(user?.name || "")}
          </Avatar>
          {size.md && (
            <Flex
              vertical
              style={{
                color: colorToken?.colorTextBase,
              }}
            >
              {isLoading ? (
                <>
                  <Skeleton.Input
                    active
                    size="small"
                    style={{ width: 120, height: 16 }}
                  />
                  <Skeleton.Input
                    active
                    size="small"
                    style={{ width: 160, height: 14, marginTop: 2 }}
                  />
                </>
              ) : (
                <>
                  <Typography.Text
                    style={{
                      color: colorToken?.colorTextBase,
                      fontSize: "14px",
                      lineHeight: "1.2",
                    }}
                  >
                    {user?.name || "User"}
                  </Typography.Text>
                  <Typography.Text
                    style={{
                      color: colorToken?.colorTextSecondary,
                      fontSize: "12px",
                      lineHeight: "1.2",
                    }}
                  >
                    {user?.email || ""}
                  </Typography.Text>
                </>
              )}
            </Flex>
          )}
          <DownOutlined
            style={{
              fontSize: "10px",
              color: colorToken?.colorTextTertiary,
              marginLeft: "4px",
            }}
          />
        </Flex>
      </Dropdown>
    </Flex>
  );
};
