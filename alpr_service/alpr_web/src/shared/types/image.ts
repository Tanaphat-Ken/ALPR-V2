type ProcessedImage = {
  image: string | null;
  plateCropImage: string | null;
  carBbox: number[][] | null;
  plateBbox: number[][] | null;
  plateId: string | null;
  province: string | null;
  timeStamp: string;
};

export type { ProcessedImage };
