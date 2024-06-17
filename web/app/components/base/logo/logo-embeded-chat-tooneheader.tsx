import type { FC } from 'react'

type LogoEmbededChatHeaderProps = {
  className?: string
}
const LogoEmbededChatTooneHeader: FC<LogoEmbededChatHeaderProps> = ({
  className,
}) => {
  return (
    // 
    <img
      src='/logo/toone-chat.png'
      className={`block w-auto h-15 ${className}`}
      alt='logo'
    />
  )
}

export default LogoEmbededChatTooneHeader
