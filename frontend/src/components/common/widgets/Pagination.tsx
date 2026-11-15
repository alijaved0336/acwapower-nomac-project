import React, { FC, useMemo, useCallback, useState, useEffect } from "react";
import {
  Pagination as AntPagination,
  PaginationProps,
  Input,
  theme,
} from "antd";

const Pagination: FC<PaginationProps> = (props) => {
  const { total = 0, pageSize = 10, current = 1, onChange } = props;
  const { token } = theme.useToken();

  const totalPages = useMemo(
    () => Math.ceil(total / pageSize),
    [total, pageSize]
  );

  const [gotoValue, setGotoValue] = useState("");

  useEffect(() => {
    setGotoValue(current.toString());
  }, [current]);

  const handleGoToPage = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        const value = parseInt(gotoValue, 10);

        if (!isNaN(value)) {
          let targetPage = value;

          if (value < 1) targetPage = 1;
          else if (value > totalPages) targetPage = totalPages;

          onChange?.(targetPage, pageSize);
          setGotoValue(targetPage.toString());
        }
      }
    },
    [gotoValue, onChange, pageSize, totalPages]
  );

  return (
    <>
      <style>{`
        .pagination-wrapper {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 16px;
        }

        .pagination-wrapper .ant-pagination-item-active a {
          color: #fff !important;
        }

        .pagination-left {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 0.875rem;
          padding-top: 1.25rem;
        }

        .pagination-left .go-to-input {
          width: 60px;
          text-align: center;
        }

        .pagination-left .total-text {
          margin-left: 8px;
        }

        .pagination-right {
          display: flex;
          align-items: center;
          gap: 8px;
          padding-top: 20px;
        }

        @media (max-width: 768px) {
          .pagination-wrapper {
            flex-direction: column;
          }

          .pagination-left,
          .pagination-right {
            width: 100%;
            justify-content: center;
          }
        }
      `}</style>

      <div className="pagination-wrapper">
        {/* Left Section */}
        <div
          className="pagination-left"
          style={{
            color: token.colorText,
          }}
        >
          <span style={{ fontWeight: "bold" }}>Go to Page</span>
          <Input
            aria-label="Go to page number"
            type="number"
            min={1}
            max={totalPages}
            className="go-to-input"
            value={gotoValue}
            onChange={(e) => setGotoValue(e.target.value)}
            onKeyDown={handleGoToPage}
          />
          <span
            className="total-text"
            style={{ color: token.colorTextSecondary }}
          >
            Total {total} rows
          </span>
        </div>

        {/* Right Section */}
        <div className="pagination-right">
          <AntPagination
            {...props}
            showTotal={undefined}
            showQuickJumper={props.showQuickJumper ?? false}
            showSizeChanger={props.showSizeChanger ?? true}
            simple={props.simple ?? false}
          />
        </div>
      </div>
    </>
  );
};

export default React.memo(Pagination);
