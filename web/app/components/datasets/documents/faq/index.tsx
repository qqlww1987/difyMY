'use client'
import type { FC } from 'react'
import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import CSVUploader from './faquploader'
import CSVDownloader from './faqdownloader'
import Button from '@/app/components/base/button'
import Modal from '@/app/components/base/modal'
import { XClose } from '@/app/components/base/icons/src/vender/line/general'
import Toast from '@/app/components/base/toast'
import { annotationBatchImport, checkAnnotationBatchImportProgress } from '@/service/annotation'
import { annotationConvertFaq } from '@/service/common'
import { useProviderContext } from '@/context/provider-context'
import AnnotationFull from '@/app/components/billing/annotation-full'
import { API_PREFIX, IS_CE_EDITION, PUBLIC_API_PREFIX } from '@/config'
export enum ProcessStatus {
  WAITING = 'waiting',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  ERROR = 'error',
}

export type IBatchModalProps = {
  appId: string
  isShow: boolean
  onCancel: () => void
  onAdded: () => void
}

const FAQModal: FC<IBatchModalProps> = ({
  appId,
  isShow,
  onCancel,
  onAdded,
}) => {
  const { t } = useTranslation()
  const { plan, enableBilling } = useProviderContext()
  const isAnnotationFull = (enableBilling && plan.usage.annotatedResponse >= plan.total.annotatedResponse)
  const [currentCSV, setCurrentCSV] = useState<File>()
  const [downLoadCSV, setdownLoadCSV] = useState<string>()
  const handleFile = (file?: File) => setCurrentCSV(file)

  useEffect(() => {
    if (!isShow)
      setCurrentCSV(undefined)
  }, [isShow])

  const [importStatus, setImportStatus] = useState<ProcessStatus | string>()
  const notify = Toast.notify
  const checkProcess = async (jobID: string) => {
    try {
      const res = await checkAnnotationBatchImportProgress({ jobID, appId })
      setImportStatus(res.job_status)
      if (res.job_status === ProcessStatus.WAITING || res.job_status === ProcessStatus.PROCESSING)
        setTimeout(() => checkProcess(res.job_id), 2500)
      if (res.job_status === ProcessStatus.ERROR)
        notify({ type: 'error', message: `${t('appAnnotation.batchModal.runError')}` })
      if (res.job_status === ProcessStatus.COMPLETED) {
        notify({ type: 'success', message: `${t('appAnnotation.batchModal.completed')}` })
        onAdded()
        onCancel()
      }
    }
    catch (e: any) {
      notify({ type: 'error', message: `${t('appAnnotation.batchModal.runError')}${'message' in e ? `: ${e.message}` : ''}` })
    }
  }

  const runBatch = async (docx: File) => {
    const formData = new FormData()
    formData.append('file', docx)
    let url="/enterprise/convert-faq"
    const urlPrefix =  API_PREFIX
    let urlWithPrefix = `${urlPrefix}${url.startsWith('/') ? url : `/${url}`}`
    try {
      // const response = await fetch(urlWithPrefix, {
      //   method: 'POST',
      //   mode: 'cors',
      // });

      // if (response.ok) {
      //   const blob = await response.blob();
      //   const url = URL.createObjectURL(blob);
      //   const link = document.createElement('a');
      //   link.href = url;
      //   link.download = 'output.csv'; // 设置文件名
      //   link.click();
      //   URL.revokeObjectURL(url);
      // } else {
      //   throw new Error('Failed to convert and download file');
      // }
      const res = await annotationConvertFaq({
        url: '/enterprise/convert-faq',
        body: formData,
      })
      console.log(res)
      // if (res.ok) {
      //   const blob = await res.blob();
      //   const url = URL.createObjectURL(blob);
      //   const link = document.createElement('a');
      //   link.href = url;
      //   link.download = 'converted.csv';
      //   link.click();
      //   URL.revokeObjectURL(url);
      // } else {
      //   const data = await res.json();
      //   throw new Error(data.error);
      // }
      // setdownLoadCSV(res.filePath)
      // 获取res 的filePath属性值
      // setImportStatus(res.job_status)
      // checkProcess(res.job_id)
    }
    catch (e: any) {
      console.log(e)
      notify({ type: 'error', message: `${t('appAnnotation.batchModal.runError')}${'message' in e ? `: ${e.message}` : ''}` })
    }
  }

  const handleSend = () => {
    if (!currentCSV)
      return
    runBatch(currentCSV)
  }

  return (
    <Modal isShow={isShow} onClose={() => { }} wrapperClassName='!z-[20]' className='px-8 py-6 !max-w-[520px] !rounded-xl'>
      <div className='relative pb-1 text-xl font-medium leading-[30px] text-gray-900'>{t('转换FAQ文件')}</div>
      <div className='absolute right-4 top-4 p-2 cursor-pointer' onClick={onCancel}>
        <XClose className='w-4 h-4 text-gray-500' />
      </div>
      <CSVUploader
        file={currentCSV}
        updateFile={handleFile}
      />
      {/* <CSVDownloader /> */}

      {isAnnotationFull && (
        <div className='mt-4'>
          <AnnotationFull />
        </div>
      )}

      <div className='mt-[28px] pt-6 flex justify-end'>
        <Button className='mr-2 text-gray-700 text-sm font-medium' onClick={onCancel}>
          {t('appAnnotation.batchModal.cancel')}
        </Button>
        <Button
          className='text-sm font-medium'
          type="primary"
          onClick={handleSend}
          disabled={!currentCSV}
          loading={importStatus === ProcessStatus.PROCESSING || importStatus === ProcessStatus.WAITING}
        >
          {t('appAnnotation.batchModal.run')}
        </Button>
      </div>
    </Modal>
  )
}
export default React.memo(FAQModal)
