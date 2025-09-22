from sqlalchemy import Column, Integer, String, Float, TIMESTAMP
from sqlalchemy.orm import relationship
from Configs.dbconfig import Base
from sqlalchemy.ext.asyncio import AsyncSession

# from Models.user_subscription import UserSubscription


class Plate_bbox(Base):
    __tablename__ = "plate_bbox"

    plate_bbox_id = Column(Integer, primary_key=True)
    top_left_x = Column(Float, nullable=True)
    top_left_y = Column(Float, nullable=True)
    top_right_x = Column(Float, nullable=True)
    top_right_y = Column(Float, nullable=True)
    bottom_left_x = Column(Float, nullable=True)
    bottom_left_y = Column(Float, nullable=True)
    bottom_right_x = Column(Float, nullable=True)
    bottom_right_y = Column(Float, nullable=True)

    api_image_logs = relationship("ApiImageLogs", back_populates="plate_bbox")

    @staticmethod
    async def process_plate_bbox(plate_bbox, db: AsyncSession):
        """
        Processes the plate_bbox data by validating and then inserting it into the database.
        """
        # Validate the plate_bbox data
        if not plate_bbox or len(plate_bbox) != 4:
            raise ValueError(
                "Invalid plate_bbox data. It must contain exactly 4 coordinates."
            )

        # Ensure each coordinate is a list of two floats
        for coord in plate_bbox:
            if not isinstance(coord, list) or len(coord) != 2:
                raise ValueError(
                    f"Invalid coordinate format: {coord}. Each must be a list of two floats."
                )

        # Pass the data to the insert function
        return await Plate_bbox.insert_plate_bbox(plate_bbox, db)

    @staticmethod
    async def insert_plate_bbox(plate_bbox_data, db: AsyncSession):
        """
        Inserts the plate_bbox data into the Plate_bbox table.
        """
        try:
            # Extract coordinates
            top_left_x, top_left_y = plate_bbox_data[0]
            top_right_x, top_right_y = plate_bbox_data[1]
            bottom_right_x, bottom_right_y = plate_bbox_data[2]
            bottom_left_x, bottom_left_y = plate_bbox_data[3]

            # Create a new Plate_bbox object
            plate_bbox_entry = Plate_bbox(
                top_left_x=top_left_x,
                top_left_y=top_left_y,
                top_right_x=top_right_x,
                top_right_y=top_right_y,
                bottom_right_x=bottom_right_x,
                bottom_right_y=bottom_right_y,
                bottom_left_x=bottom_left_x,
                bottom_left_y=bottom_left_y
            )

            # Add to session and commit
            db.add(plate_bbox_entry)
            await db.commit()
            await db.refresh(plate_bbox_entry)

            return {"message": "Plate_bbox inserted successfully", "plate_bbox_id": plate_bbox_entry.plate_bbox_id}

        except Exception as e:
            await db.rollback()
            raise ValueError(f"Failed to insert plate_bbox: {str(e)}")
