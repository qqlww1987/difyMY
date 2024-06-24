import type { FC } from 'react'

type LogoEmbededChatAvatarProps = {
  className?: string
}
const LogoTooneEmbededChatAvatar: FC<LogoEmbededChatAvatarProps> = ({
  className,
}) => {
  return (
    <img
      // src='/logo/chatRobot.ico'
      src='/logo/toone-chat-robot.png'
      className={`block w-10 h-10 ${className}`}
      alt='logo'
    />
  )
}

export default LogoTooneEmbededChatAvatar
