
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
const valueFormatter = (v: string | number) => v
const COLOR_TYPE_MAP = {
  green: {
    lineColor: 'rgba(6, 148, 162, 1)',
    bgColor: ['rgba(6, 148, 162, 0.2)', 'rgba(67, 174, 185, 0.08)'],
  },
  orange: {
    lineColor: 'rgba(255, 138, 76, 1)',
    bgColor: ['rgba(254, 145, 87, 0.2)', 'rgba(255, 138, 76, 0.1)'],
  },
  blue: {
    lineColor: 'rgba(28, 100, 242, 1)',
    bgColor: ['rgba(28, 100, 242, 0.3)', 'rgba(28, 100, 242, 0.1)'],
  },
}

const COMMON_COLOR_MAP = {
  label: '#9CA3AF',
  splitLineLight: '#F3F4F6',
  splitLineDark: '#E5E7EB',
}

type IColorType = 'green' | 'orange' | 'blue'
type IChartType = 'conversations' | 'endUsers' | 'costs' | 'workflowCosts'
type IChartConfigType = { colorType: IColorType; showTokens?: boolean }

const commonDateFormat = 'MMM D, YYYY'

const CHART_TYPE_CONFIG: Record<string, IChartConfigType> = {
  conversations: {
    colorType: 'green',
  },
  endUsers: {
    colorType: 'orange',
  },
  costs: {
    colorType: 'blue',
    showTokens: true,
  },
  workflowCosts: {
    colorType: 'blue',
  },
}
interface BarChartProps {
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

const BarChart: React.FC<BarChartProps> = ({ data,style,basicInfo ,className,chartType }) => {
  
  const newData = data.map(item => ({
    value: item.count,
    name: item.word,
  }));
  
  const options: EChartsOption = {
    tooltip: {
    trigger: 'item'
  },
  grid: { top: 8, right: 36, bottom: 0, left: 0, containLabel: true },
  legend: {
    top: '5%',
    orient: 'vertical',
    left: 'left'
  },
  position: 'bottom',
  series: [
    {
      name: '最常访问',
      type: 'pie',
      bottom: 5,
      radius: ['70%', '88%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 40,
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: newData,
    }
  ]
  };
  
  return (
    <div className={`flex flex-col w-full px-6 py-4 border-[0.5px] rounded-lg border-gray-200 shadow-xs ${className ?? ''}`}>
      <div className='mb-3'>
        <Basic name={basicInfo.title} type={basicInfo.timePeriod} hoverTip={basicInfo.explanation} />
      </div>
      <div className='mb-4 flex-1'>
        <Basic
          isExtraInLine={CHART_TYPE_CONFIG[chartType].showTokens}
          name={'热度显示'}
          type={!CHART_TYPE_CONFIG[chartType].showTokens
            ? ''
            : <span>{t('appOverview.analysis.tokenUsage.consumed')} Tokens<span className='text-sm'>
              <span className='ml-1 text-gray-500'>(</span>
              {/* <span className='text-orange-400'>~{sum(statistics.map(item => parseFloat(get(item, 'total_price', '0')))).toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 4 })}</span> */}
              <span className='text-gray-500'>)</span>
            </span></span>}
       
           />
      </div>
      <ReactECharts option={options} style={{ height: 160}} />
    </div>
  )
}
export const FrequentKeywords: FC<IBizChartProps> = ({ id, period }) => {
  const { t } = useTranslation()
  const { data: response } = useSWR({ url: `/apps/${id}/statistics/frequent-keywords`, params: period.query }, getAppFrequentKeywords)
  if (!response)
    return <Loading />
  const noDataFlag = !response.data || response.data.length === 0
  return <BarChart
    data={response.data.map(item => ({
      date: [dayjs(item.date).format('YYYY-MM-DD'), dayjs(item.date).format('HH:mm:ss')],
      word: item.word,
      count: item.count,
    }))}
    style={{ height: 160 }}
    basicInfo={{ title: t('Top10访问关键词'), explanation: t('反映当前智能体访问频率最高的关键词'), timePeriod: period.name }} chartType={'conversations'}    
  />
}
export default BarChart;
