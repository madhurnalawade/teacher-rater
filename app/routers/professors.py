from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app import schemas
from app.access import is_admin_user
from app.db import get_db
from app.dependencies import get_admin_user, get_current_user, get_optional_user
from app.models import Professor, Review, User


router = APIRouter(prefix="/api", tags=["professors"])


@router.get("/professors", response_model=list[schemas.ProfessorRead])
def list_professors(db: Session = Depends(get_db)):
    stmt = (
        select(
            Professor.id,
            Professor.name,
            Professor.department,
            Professor.photo_url,
            Professor.created_at,
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(Review, Review.professor_id == Professor.id)
        .group_by(Professor.id)
        .order_by(Professor.name.asc())
    )
    rows = db.execute(stmt).all()

    return [
        schemas.ProfessorRead(
            id=row.id,
            name=row.name,
            department=row.department,
            photo_url=row.photo_url,
            created_at=row.created_at,
            average_rating=float(row.average_rating) if row.average_rating is not None else None,
            review_count=int(row.review_count),
        )
        for row in rows
    ]


@router.post(
    "/professors",
    response_model=schemas.ProfessorRead,
    status_code=status.HTTP_201_CREATED,
)
def create_professor(
    payload: schemas.ProfessorCreate,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(get_admin_user),
):

    existing = db.execute(
        select(Professor).where(func.lower(Professor.name) == payload.name.lower())
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="A professor with this name already exists.")

    professor = Professor(name=payload.name, department=payload.department, photo_url=payload.photo_url)
    db.add(professor)
    db.commit()
    db.refresh(professor)

    return schemas.ProfessorRead(
        id=professor.id,
        name=professor.name,
        department=professor.department,
        photo_url=professor.photo_url,
        created_at=professor.created_at,
        average_rating=None,
        review_count=0,
    )


@router.delete("/professors/{professor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_professor(
    professor_id: int,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(get_admin_user),
):
    professor = db.get(Professor, professor_id)
    if professor is None:
        raise HTTPException(status_code=404, detail="Professor not found.")

    db.delete(professor)
    db.commit()


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(get_admin_user),
):
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found.")

    db.delete(review)
    db.commit()


@router.get("/professors/{professor_id}", response_model=schemas.ProfessorDetails)
def get_professor_details(
    professor_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    stmt = (
        select(Professor)
        .where(Professor.id == professor_id)
        .options(selectinload(Professor.reviews).selectinload(Review.reviewer))
    )
    professor = db.execute(stmt).scalar_one_or_none()

    if professor is None:
        raise HTTPException(status_code=404, detail="Professor not found.")

    reviews_sorted = sorted(
        professor.reviews,
        key=lambda review: review.created_at,
        reverse=True,
    )

    can_view_reviewer_emails = is_admin_user(current_user)

    review_models = [
        schemas.ReviewRead(
            id=review.id,
            rating=review.rating,
            review_text=review.review_text,
            created_at=review.created_at,
            reviewer=schemas.UserPublic(
                id=review.reviewer.id,
                username=review.reviewer.username or "anonymous",
                email=review.reviewer.email if can_view_reviewer_emails else None,
            ),
        )
        for review in reviews_sorted
    ]

    average_rating = None
    if reviews_sorted:
        average_rating = round(sum(review.rating for review in reviews_sorted) / len(reviews_sorted), 2)

    return schemas.ProfessorDetails(
        id=professor.id,
        name=professor.name,
        department=professor.department,
        photo_url=professor.photo_url,
        created_at=professor.created_at,
        average_rating=average_rating,
        review_count=len(reviews_sorted),
        reviews=review_models,
    )


@router.post(
    "/professors/{professor_id}/reviews",
    response_model=schemas.ReviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    professor_id: int,
    payload: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Set a username before posting reviews.",
        )

    professor = db.get(Professor, professor_id)
    if professor is None:
        raise HTTPException(status_code=404, detail="Professor not found.")

    existing = db.execute(
        select(Review).where(
            Review.professor_id == professor_id,
            Review.user_id == current_user.id,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="You already reviewed this professor.")

    review = Review(
        rating=payload.rating,
        review_text=payload.review_text,
        user_id=current_user.id,
        professor_id=professor.id,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return schemas.ReviewRead(
        id=review.id,
        rating=review.rating,
        review_text=review.review_text,
        created_at=review.created_at,
        reviewer=schemas.UserPublic(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email if is_admin_user(current_user) else None,
        ),
    )
