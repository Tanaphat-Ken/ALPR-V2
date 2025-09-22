const isExpired = (dateStr: string): boolean => {
  const date = new Date(dateStr)

  if (isNaN(date.getTime())) return true

  const today = new Date()
  today.setHours(0, 0, 0, 0)

  return date < today
}

const convertToDateString = (dateStr: string): string => {
  const date = new Date(dateStr)
  
  if (isNaN(date.getTime())) return ''

  const year = date.getFullYear()
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')

  return `${year}/${month}/${day}`
}

const padZero = (num: number) => num.toString().padStart(2, '0')

const convertToReadableTimeStamp = (dateStr: string): string => {
  const date = new Date (dateStr)

  const year = date.getFullYear()
  const month = padZero(date.getMonth() + 1)
  const day = padZero(date.getDate())

  const hours = padZero(date.getHours())
  const minutes = padZero(date.getMinutes())
  const seconds = padZero(date.getSeconds())

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

export { isExpired, convertToDateString, convertToReadableTimeStamp }