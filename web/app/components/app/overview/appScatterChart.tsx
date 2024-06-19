
// import React from 'react';
// import ReactECharts from 'echarts-for-react';
// import { EChartsOption } from 'echarts';
'use client'
import type { FC } from 'react'
import React from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import useSWR from 'swr'
import dayjs from 'dayjs'
import { get } from 'lodash-es'
import { useTranslation } from 'react-i18next'
import { formatNumber } from '@/utils/format'
import Basic from '@/app/components/app-sidebar/basic' 
import Loading from '@/app/components/base/loading'
import type { AppFrequentKeywordsResponse } from '@/models/app'
import { getAppFrequentKeywords } from '@/service/apps'

type IChartType = 'conversations' | 'endUsers' | 'costs' | 'workflowCosts'


interface ChartProps {
  data: Array<{
    date: string[];
    word: string;
    count: number;
  }>;
  style: React.CSSProperties;
  basicInfo: { title: string; explanation: string; timePeriod: string };
  className?: string;
  chartType: IChartType;
}
export type PeriodParams = {
  name: string
  query?: {
    start: string
    end: string
  }
}
export type IBizChartProps = {
  period: PeriodParams
  id: string
}

const ScatterChart: React.FC<ChartProps> = ({ data,style,basicInfo ,className,chartType }) => {
  
  const newData = data.map(item => ({
    x: item.word,
          y: item.count,
          value: item.count
  }));
  // 计算气泡大小的最小值和最大值
const minSize = Math.min(...data.map(item => item.count));
const maxSize = Math.max(...data.map(item => item.count));
  const options: EChartsOption = {
    // grid: {
    //   bottom: '3%',
    //   containLabel: true,
    // },
    // grid: { top: 8, right: 36, bottom: 0, left: 0, containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(item => item.word),
      position: 'bottom',
      show: false,
    },
    yAxis: {
      type: 'value',
      show: false,
    },
    // grid: {  right: 36, bottom: 0, left: 0, containLabel: true },
    series: [
      {
        type: 'scatter',
        // data: newData,  
        data: data.map(item => [item.word, item.count]),
        symbolSize: (value: any) => {
          // 根据数据大小计算气泡大小
          const size = (value[1] - minSize) / (maxSize - minSize) * 50 + 10;
          return size;
        },
        itemStyle: {
          color: (params: any) => {
            // 为每个数据点分别设置颜色
            return `rgb(${Math.floor(Math.random() * 256)}, ${Math.floor(Math.random() * 256)}, ${Math.floor(Math.random() * 256)})`;
          },
        },
        emphasis: {
          label: {
            show: true,
            position: 'top',
            //  formatter: '{b}\n{c}',
          },
        },
      },
   ],
  };
  
  return (
    <div className={`flex flex-col w-full px-6 py-4 border-[0.5px] rounded-lg border-gray-200 shadow-xs ${className ?? ''}`}>
      <div className='mb-3'>
        <Basic name={basicInfo.title} type={basicInfo.timePeriod} hoverTip={basicInfo.explanation} />
      </div>
  
      <ReactECharts option={options} style={{ height: 160}} />
    </div>
  )
}
export const FrequentKeywordsNew: FC<IBizChartProps> = ({ id, period }) => {
  const { t } = useTranslation()
  const { data: response } = useSWR({ url: `/apps/${id}/statistics/frequent-keywords`, params: period.query }, getAppFrequentKeywords)
  if (!response)
    return <Loading />
  const noDataFlag = !response.data || response.data.length === 0
  return <ScatterChart
    data={response.data.map(item => ({
      date: [dayjs(item.date).format('YYYY-MM-DD'), dayjs(item.date).format('HH:mm:ss')],
      word: item.word,
      count: item.count,
    }))}
    style={{ height: 160 }}
    basicInfo={{ title: t('Top10访问关键词'), explanation: t('反映当前智能体访问频率最高的关键词'), timePeriod: period.name }} chartType={'conversations'}    
  />
}
export default ScatterChart;
