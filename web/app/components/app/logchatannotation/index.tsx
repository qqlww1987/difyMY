'use client'
import type { FC } from 'react'
import React from 'react'
import cn from 'classnames'
import { useTranslation } from 'react-i18next'
import { useRouter } from 'next/navigation'
import Log from '@/app/components/app/log'
import WorkflowLog from '@/app/components/app/workflow-log'
import Annotation from '@/app/components/app/annotation'
import Loading from '@/app/components/base/loading'
import { PageType } from '@/app/components/app/configuration/toolbox/annotation/type'
import TabSlider from '@/app/components/base/tab-slider-plain'
import { useStore as useAppStore } from '@/app/components/app/store'

type Props = {
  pageType: PageType
  conversation_id:string
}

const LogChatAnnotation: FC<Props> = ({
  pageType,
  conversation_id
}) => {
  const { t } = useTranslation()
  const router = useRouter()
  const appDetail = useAppStore(state => state.appDetail)

  const options = [
    { value: PageType.log, text: t('appLog.title') },
    { value: PageType.annotation, text: t('appAnnotation.title') },
  ]

  if (!appDetail) {
    return (
      <div className='flex h-full items-center justify-center bg-white'>
        <Loading />
      </div>
    )
  }

  return (
    <div className='pt-4 px-6 h-full flex flex-col'>
      {appDetail.mode !== 'workflow' && (
        <TabSlider
          className='shrink-0'
          value={pageType}
          onChange={(value) => {
            router.push(`/app/${appDetail.id}/${value === PageType.log ? 'logs' : 'annotations'}`)
          }}
          options={options}
        />
      )}
      <div className={cn('grow', appDetail.mode !== 'workflow' && 'mt-3')}>
        {pageType === PageType.log && appDetail.mode !== 'workflow' && (<Log appDetail={appDetail} />)}
        {pageType === PageType.annotation && (<Annotation appDetail={appDetail} />)}
        {pageType === PageType.log && appDetail.mode === 'workflow' && (<WorkflowLog appDetail={appDetail} />)}
      </div>
    </div>
  )
}
export default React.memo(LogChatAnnotation)
