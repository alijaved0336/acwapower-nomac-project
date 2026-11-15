"use client";
import React, { useMemo } from "react";
import { Card, Row, Col, Typography } from "antd";
import { useSimpleStock } from "../../context/StockContext";
import { useGetChemicalStockQuery } from "@/store/api/chemicalApi";
import { processChemicalData, isPlaceholder } from "../../utils/stockUtils";
import {
  renderSkeletonCards,
  renderEmptyCards,
  renderDataRow,
} from "../../utils/stockHelpers";
import { useStockStyles, colProps } from "../../utils/stockStyles";
import { formatColumnTitle } from "../../../../../../utils/tableConfig";
import { useApiNotifications } from "../../../../../../hooks/useApiNotifications";
import { cn } from "@/utils/cn";
import layoutStyles from "../../styles/stockLayout.module.css";

const { Text } = Typography;

const StockCards: React.FC = () => {
  const { selectedSiteName } = useSimpleStock();
  const {
    containerStyle,
    cardBodyStyle,
    titleStyle,
    dataRowStyle,
    labelStyle,
    valueStyle,
    dimValueStyle,
    unitStyle,
  } = useStockStyles();
  const { data, isLoading, isFetching } = useGetChemicalStockQuery(
    { site_id: selectedSiteName },
    { skip: !selectedSiteName }
  );

  const showLoading = isLoading || isFetching || !selectedSiteName;
  const hasData =
    data?.success &&
    data?.data?.chemicals &&
    Object.keys(data.data.chemicals).length > 0;

  const apiConfigs = useMemo(
    () => [
      {
        key: "chemical",
        name: "Chemical Stock",
        data_availability_for_given_date:
          data?.data.data_availability_for_given_date,
        from_date: data?.data.from_date,
        to_date: data?.data.to_date,
        isLoading: isLoading,
        isFetching: isFetching,
      },
    ],
    [
      data?.data.data_availability_for_given_date,
      data?.data.from_date,
      data?.data.to_date,
      isLoading,
      isFetching,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  return (
    <div style={containerStyle}>
      {showLoading ? (
        renderSkeletonCards(6, colProps, {}, cardBodyStyle, dataRowStyle)
      ) : !hasData ? (
        renderEmptyCards(
          6,
          colProps,
          {},
          cardBodyStyle,
          dimValueStyle.color as string
        )
      ) : (
        <Row gutter={[12, 12]}>
          {processChemicalData(data.data.chemicals).map((chemical, index) => (
            <Col {...colProps} key={chemical.name || index}>
              <Card
                className={cn(layoutStyles.stockCard)}
                styles={{ body: cardBodyStyle }}
              >
                <Text style={titleStyle}>
                  {formatColumnTitle(chemical.name)}
                </Text>
                <div>
                  {chemical.data.map((item, idx) =>
                    renderDataRow(
                      item,
                      idx,
                      dataRowStyle,
                      labelStyle,
                      valueStyle,
                      dimValueStyle,
                      unitStyle,
                      isPlaceholder
                    )
                  )}
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
};

export default StockCards;
