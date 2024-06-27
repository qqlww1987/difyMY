
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
import { log } from 'console'
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
  allcount:number;
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

const BarChart: React.FC<BarChartProps> = ({ data,allcount,style,basicInfo ,className,chartType }) => {
  
  const newData = data.map(item => ({
    value: item.count,
    name: item.word,
  }));
  
  const newDataLength = newData.reduce((acc, cur) => acc + cur.value, 0);
  console.log("前十数据为："+newDataLength)
  const percentage = (newDataLength / allcount) * 100;
  const options: EChartsOption = {
    tooltip: {
    trigger: 'item'
    
  },
  
  grid: { top: 8, right: 36, bottom: 0, left: 0, containLabel: true },
  legend: {
    top: '5%',
     // 过长显示省略号
     formatter: function (params) {
       return params.length > 16 ? params.slice(0, 16) + '...' : params;
     },
    orient: 'vertical',
    left: 'left'
  },
  position: 'bottom',
  series: [
    {
      name: '最常访问',
      type: 'pie',
      bottom: 5,
      // radius: '50%',
      radius: ['70%', '88%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      left: '40%', // 将饼图向右对齐
      label: {
        show: false,
        formatter: function (params) {
          const total = newData.reduce((acc, cur) => acc + cur.value, 0);
            const percentage = (Number(params.value) / total * 100).toFixed(2) + '%';
            const name=params.name.length > 10 ? params.name.slice(0, 10) + '...' : params.name;
            return `${name}\n${(percentage)}`;
          // return params.name.length > 10 ? params.name.slice(0, 10) + '...' : params.name;
        },
        position: 'center'
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        },
        label: {
          show: true,
          fontSize: 12,
          // 过长显示省略号
          formatter: function (params) {
            const total = newData.reduce((acc, cur) => acc + cur.value, 0);
            const percentage = (Number(params.value) / total * 100).toFixed(2) + '%';
            const name=params.name.length > 10 ? params.name.slice(0, 10) + '...' : params.name;
            return `${name}\n${(percentage)}`;
          },
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
  console.log("整个数据为："+allcount)
  return (
    <div className={`flex flex-col w-full px-6 py-4 border-[0.5px] rounded-lg border-gray-200 shadow-xs ${className ?? ''}`}>
      <div className='mb-3'>
        <Basic name={basicInfo.title} type={basicInfo.timePeriod} hoverTip={basicInfo.explanation} />
      </div>
      <div className='mb-4 flex-1'>
        <Basic
          isExtraInLine={CHART_TYPE_CONFIG[chartType].showTokens}
          // newData的个数占比allcount
          name={`高频问题占比 (${percentage.toFixed(2)}%)`}
          // name={'高频问题'}
          type={!CHART_TYPE_CONFIG[chartType].showTokens
            ? ''
            : <span>{t('appOverview.analysis.tokenUsage.consumed')} Tokens<span className='text-sm'>
              <span className='ml-1 text-gray-500'>(</span>
              {/* <span className='text-orange-400'>~{sum(statistics.map(item => parseFloat(get(item, 'total_price', '0')))).toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 4 })}</span> */}
              <span className='text-gray-500'>)</span>
            </span></span>}
            textStyle={{ main: `!text-3xl !font-normal '!text-gray-300'` }} 
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
    
     allcount={response.count}
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
