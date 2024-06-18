'use client'
import { useState } from 'react'
import useSWR from 'swr'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useContext } from 'use-context-selector'
import { UserPlusIcon } from '@heroicons/react/24/outline'
import { useTranslation } from 'react-i18next'
import { fetchMembers } from '@/service/common'
import I18n from '@/context/i18n'
import { useAppContext } from '@/context/app-context'
import LogoEmbededChatHeader from '@/app/components/base/logo/logo-embeded-chat-header'
import { useProviderContext } from '@/context/provider-context'
import { Plan } from '@/app/components/billing/type'
import { NUM_INFINITE } from '@/app/components/billing/config'
import { LanguagesSupported } from '@/i18n/language'
import { ToastContext } from '@/app/components/base/toast'
import { removeWorkspaceNew } from '@/service/common'
import { useWorkspacesContext } from '@/context/workspace-context'
dayjs.extend(relativeTime)

const MorePage = () => {
  const { t } = useTranslation()
  const { locale } = useContext(I18n)
  const { notify } = useContext(ToastContext)
  const { userProfile, currentWorkspace, isCurrentWorkspaceManager } = useAppContext()
  const { data, mutate } = useSWR({ url: '/workspaces/current/members' }, fetchMembers)
  const accounts = data?.accounts || []
  const owner = accounts.filter(account => account.role === 'owner')?.[0]?.email === userProfile.email
  const { plan, enableBilling } = useProviderContext()
  const isNotUnlimitedMemberPlan = enableBilling && plan.type !== Plan.team && plan.type !== Plan.enterprise
  const isMemberFull = enableBilling && isNotUnlimitedMemberPlan && accounts.length >= plan.total.teamMembers
  const removeWorkspace = async () => {
    try {
        if (owner==false)
        {
            notify({ type: 'error', message: t('您不是工作空间管理员，无法删除工作空间') })
            return
        }
        var tenant_id= currentWorkspace.id 
        console.log(tenant_id)
        await removeWorkspaceNew({ url: '/enterprise/workspaceRemove', body: { tenant_id:tenant_id} })
        notify({ type: 'success', message: t('删除工作空间成功') })
        location.assign(`${location.origin}`)
    }
    catch (e) {
      // 打印错误 e
      console.error('发生错误:', e)
      notify({ type: 'error', message: t('创建工作空间失败') })
    }
  } 
  return (
    <>
      <div className='flex flex-col'>
        <div className='flex items-center mb-4 p-3 bg-gray-50 rounded-2xl'>
          <LogoEmbededChatHeader className='!w-10 !h-10' />
          <div className='grow mx-2'>
            <div className='text-sm font-medium text-gray-900'>{currentWorkspace?.name}</div>
            {enableBilling && (
              <div className='text-xs text-gray-500'>
                {isNotUnlimitedMemberPlan
                  ? (
                    <div className='flex space-x-1'>
                      <div>{t('billing.plansCommon.member')}{locale !== LanguagesSupported[1] && accounts.length > 1 && 's'}</div>
                      <div className='text-gray-700'>{accounts.length}</div>
                      <div>/</div>
                      <div>{plan.total.teamMembers === NUM_INFINITE ? t('billing.plansCommon.unlimited') : plan.total.teamMembers}</div>
                    </div>
                  )
                  : (
                    <div className='flex space-x-1'>
                      <div>{accounts.length}</div>
                      <div>{t('billing.plansCommon.memberAfter')}{locale !== LanguagesSupported[1] && accounts.length > 1 && 's'}</div>
                    </div>
                  )}
              </div>
            )}

          </div>
          <div className={
            `shrink-0 flex items-center py-[7px] px-3 border-[0.5px] border-gray-200
            text-[13px] font-medium text-primary-600 bg-white
            shadow-xs rounded-lg ${(isCurrentWorkspaceManager && !isMemberFull) ? 'cursor-pointer' : 'grayscale opacity-50 cursor-default'}`
          }  onClick={() => removeWorkspace()}>
            <UserPlusIcon className='w-4 h-4 mr-2 ' />
            {t('删除工作空间')}
          </div>
        </div>
     
      </div>
      
    </>
  )
}

export default MorePage
