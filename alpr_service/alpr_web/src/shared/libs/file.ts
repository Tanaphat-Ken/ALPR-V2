export const fileToBase64 = (file: File | Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = (error) => reject(error)
    reader.readAsDataURL(file)
  })
}

export const base64ToFile = (base64: string, fileName: string, fileType: 'image' | 'video'): File => {
  const typePrefix = fileType === 'image' ? 'image/' : 'video/'
  const mimeType = typePrefix + fileName.split('.').pop()?.toLocaleLowerCase()
  const byteString = atob(base64.split(',')[1])

  const arrayBuffer = new ArrayBuffer(byteString.length)
  const uint8Array = new Uint8Array(arrayBuffer)

  for (let i = 0; i < byteString.length; i++) {
    uint8Array[i] = byteString.charCodeAt(i)
  }

  const blob = new Blob([uint8Array], { type: mimeType })

  return new File([blob], fileName, { type: mimeType })
}

export const base64ToImage = (base64: string): Promise<HTMLImageElement> => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.src = base64
    img.onload = () => resolve(img)
    img.onerror = (err) => reject(err)
  })
}