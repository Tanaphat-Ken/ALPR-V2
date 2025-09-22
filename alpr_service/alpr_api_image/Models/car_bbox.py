from sqlalchemy import Column, Integer, String, Float, TIMESTAMP
from sqlalchemy.orm import relationship
from Configs.dbconfig import Base
from sqlalchemy.ext.asyncio import AsyncSession
# from Models.user_subscription import UserSubscription


class Car_bbox(Base):
    __tablename__ = "car_bbox"

    car_bbox_id = Column(Integer, primary_key=True)
    top_left_x = Column(Float, nullable=True)
    top_left_y = Column(Float, nullable=True)
    top_right_x = Column(Float, nullable=True)
    top_right_y = Column(Float, nullable=True)
    bottom_left_x = Column(Float, nullable=True)
    bottom_left_y = Column(Float, nullable=True)
    bottom_right_x = Column(Float, nullable=True)
    bottom_right_y = Column(Float, nullable=True)

    api_image_logs = relationship("ApiImageLogs", back_populates="car_bbox")

    @staticmethod
    async def process_car_bbox(car_bbox, db: AsyncSession):
        """
        Processes the car_bbox data by validating and then inserting it into the database.
        """
        # Validate the car_bbox data
        if not car_bbox or len(car_bbox) != 4:
            raise ValueError(
                "Invalid car_bbox data. It must contain exactly 4 coordinates."
            )

        # Ensure each coordinate is a list of two floats
        for coord in car_bbox:
            if not isinstance(coord, list) or len(coord) != 2:
                raise ValueError(
                    f"Invalid coordinate format: {coord}. Each must be a list of two floats."
                )

        # Pass the data to the insert function
        return await Car_bbox.insert_car_bbox(car_bbox, db)

    @staticmethod
    async def insert_car_bbox(car_bbox_data, db: AsyncSession):
        """
        Inserts the car_bbox data into the Car_bbox table.
        """
        try:
            # Extract coordinates
            top_left_x, top_left_y = car_bbox_data[0]
            top_right_x, top_right_y = car_bbox_data[1]
            botton_right_x, botton_right_y = car_bbox_data[2]
            botton_left_x, botton_left_y = car_bbox_data[3]

            # Create a new Car_bbox object
            car_bbox_entry = Car_bbox(
                top_left_x=top_left_x,
                top_left_y=top_left_y,
                top_right_x=top_right_x,
                top_right_y=top_right_y,
                bottom_right_x=botton_right_x,
                bottom_right_y=botton_right_y,
                bottom_left_x=botton_left_x,
                bottom_left_y=botton_left_y
            )

            # Add to session and commit
            db.add(car_bbox_entry)
            await db.commit()
            await db.refresh(car_bbox_entry)

            return {"message": "Car_bbox inserted successfully", "car_bbox_id": car_bbox_entry.car_bbox_id}

        except Exception as e:
            await db.rollback()
            raise ValueError(f"Failed to insert car_bbox: {str(e)}")
