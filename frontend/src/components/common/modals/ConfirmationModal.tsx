import React from "react";
import { Button, Modal, Spin, theme } from "antd";

interface ConfirmationModalProps {
  open: boolean;
  title?: string;
  message?: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmButtonType?: "primary" | "danger";
  loading?: boolean;
  itemName?: string;
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  open,
  title = "Are you sure you want to remove this chart?",
  message,
  confirmText = "Yes, Remove",
  cancelText = "Cancel",
  onConfirm,
  onCancel,
  confirmButtonType = "danger",
  loading = false,
  itemName,
}) => {
  const { token } = theme.useToken();

  const buttonStyle = {
    width: "164px",
    height: "42px",
    padding: "11px 16px",
    borderRadius: "8px",
    fontFamily: "Figtree",
    fontWeight: 500,
    fontSize: "14px",
    lineHeight: "20px",
    textAlign: "center" as const,
    transition: "all 0.2s",
  };

  return (
    <Modal
      open={open}
      onCancel={onCancel}
      footer={null}
      centered
      width={450}
      closable={false}
      styles={{ body: { padding: "32px 24px 24px 24px" } }}
    >
      <div style={{ textAlign: "center" }}>
        <h3
          style={{
            fontFamily: "Figtree",
            fontWeight: 500,
            fontSize: "20px",
            lineHeight: "28px",
            textAlign: "center",
            color: token.colorText,
            marginBottom: "16px",
          }}
        >
          {title}
        </h3>
        <p
          style={{
            fontFamily: "Figtree",
            fontWeight: 400,
            fontSize: "14px",
            lineHeight: "20px",
            textAlign: "center",
            color: token.colorTextSecondary,
            marginBottom: "24px",
          }}
        >
          {message ? (
            message
          ) : itemName ? (
            <>
              You are about to delete the{" "}
              <span style={{ fontWeight: 600, color: token.colorText }}>
                {itemName}
              </span>
              . This action cannot be undone. Are you sure?
            </>
          ) : (
            "This action cannot be undone. Are you sure?"
          )}
        </p>
        <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
          <Button
            variant="outlined"
            color="default"
            className="min-h-[40px] w-full max-w-[160px]"
            disabled={loading}
            onClick={onCancel}
          >
            {cancelText}
          </Button>

          <Button
            variant="outlined"
            color="danger"
            className="min-h-[40px] w-full max-w-[160px]"
            loading={loading}
            disabled={loading}
            onClick={onConfirm}
          >
            <span>{confirmText}</span>
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default ConfirmationModal;
