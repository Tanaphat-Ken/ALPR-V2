import ImageUploader from './_components/image-uploader'
import ImageFileInfo from './_components/image-file-info'
import SubmitButton from './_components/submit-button'
import ImageLogs from './_components/image-logs'

const DashboardUploadImage = () => {

  return (
    <div>
      <ImageUploader />
      <ImageFileInfo />
      <SubmitButton />
      <ImageLogs />
    </div>
  )
}

export default DashboardUploadImage