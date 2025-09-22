import type { UploadProps, GetProp } from 'antd'

export type FileType = Parameters<GetProp<UploadProps, 'beforeUpload'>>[0];
