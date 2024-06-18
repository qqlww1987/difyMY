import React from 'react'
import Main from '@/app/components/app/logchatannotation'
import { PageType } from '@/app/components/app/configuration/toolbox/annotation/type'

const LogsInfo = async () => {
  return (
    <Main pageType={PageType.log} conversation_id={''} />
  )
}

export default LogsInfo
