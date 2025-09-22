import VideoUploader from './_components/video-uploader'
import SubmitButton from './_components/submit-button'
import ImageLogs from './_components/image-logs'

const DashboardUploadVideo = () => {
  return (
    <div>
      <VideoUploader />
      <SubmitButton />
      <ImageLogs />
    </div>
  )
}

export default DashboardUploadVideo