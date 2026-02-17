type ProcessImageBody = {
  file: File
  token: string
}

type ProcessImageResponse = {
  model_response: {
    car_bbox: number[][] | null,
    plate_bbox: number[][] | null,
    plate_id: string | null,
    province: string | null,
    plate_crop_image?: string | null,
  }
}

export type {
  ProcessImageBody,
  ProcessImageResponse
}